/*
This file is part of Telegram Desktop,
the official desktop application for the Telegram messaging service.

For license and copyright information please follow this link:
https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL
*/
#include "export/export_settings.h"

#include "export/output/export_output_abstract.h"

namespace Export {
namespace {

constexpr auto kMaxFileSize = 4000 * int64(1024 * 1024);

} // namespace

bool MediaSettings::validate() const {
	if ((types | Type::AllMask) != Type::AllMask) {
		return false;
	} else if (sizeLimit < 0 || sizeLimit > kMaxFileSize) {
		return false;
	}
	for (const auto &[type, limit] : sizeLimits) {
		if ((Types(type) | Type::AllMask) != Type::AllMask
			|| limit < 0
			|| limit > kMaxFileSize) {
			return false;
		}
	}
	return true;
}

int64 MediaSettings::sizeLimitFor(Type type) const {
	const auto i = sizeLimits.find(type);
	return (i != end(sizeLimits)) ? i->second : sizeLimit;
}

void MediaSettings::setSizeLimit(Type type, int64 limit) {
	sizeLimits[type] = limit;
}

int64 MediaSettings::maxSizeLimit() const {
	auto result = int64(0);
	for (const auto type : kAllTypes) {
		if (types & type) {
			result = std::max(result, sizeLimitFor(type));
		}
	}
	return result;
}

bool Settings::validate() const {
	using Format = Output::Format;
	const auto MustBeFull = Type::PersonalChats | Type::BotChats;
	const auto MustNotBeFull = Type::PublicGroups | Type::PublicChannels;
	if ((types | Type::AllMask) != Type::AllMask) {
		return false;
	} else if ((fullChats | Type::AllMask) != Type::AllMask) {
		return false;
	} else if ((fullChats & MustBeFull) != MustBeFull) {
		return false;
	} else if ((fullChats & MustNotBeFull) != 0) {
		return false;
	} else if (format != Format::Html
		&& format != Format::Json
		&& format != Format::HtmlAndJson) {
		return false;
	} else if (!media.validate()) {
		return false;
	} else if (singlePeerTill > 0 && singlePeerTill <= singlePeerFrom) {
		return false;
	}
	return true;
};

} // namespace Export
